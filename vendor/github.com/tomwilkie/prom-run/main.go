package main

import (
	"context"
	"flag"
	"fmt"
	"html/template"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
)

var (
	statusCode = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "command_exit_code",
		Help: "Exit code of command.",
	})
	commandDuration = prometheus.NewSummary(prometheus.SummaryOpts{
		Name: "command_duration_seconds",
		Help: "Time spent running command.",
	})
)

func reap() {
	log.Debugf("Reaping children")
	var wstatus syscall.WaitStatus
	for {
		pid, err := syscall.Wait4(-1, &wstatus, 0, nil)
		if err == syscall.ECHILD {
			// No more children to reap, stop
			return
		}
		log.Debugf("Reaped child %d, wstatus=%+v, err=%v", pid, wstatus, err)
	}
}

type pair struct {
	out []byte
	err error
}

func main() {
	var (
		period     = flag.Duration("period", 10*time.Second, "Period with which to run the command.")
		timeout    = flag.Duration("timeout", 10*time.Minute, "Amount of time to give the command to run.")
		listenAddr = flag.String("listen-addr", ":9152", "Address to listen on")
	)
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s (options) command...\n", os.Args[0])
		flag.PrintDefaults()
	}
	flag.Parse()
	if len(flag.Args()) <= 0 {
		flag.Usage()
		os.Exit(2)
	}
	command := flag.Args()[0]
	args := flag.Args()[1:]

	var (
		outputLock      sync.Mutex
		outputBuf       []byte
		lastRunStart    time.Time
		lastRunDuration time.Duration
		withLock        = func(f func()) {
			outputLock.Lock()
			defer outputLock.Unlock()
			f()
		}
	)

	go func() {
		for range time.Tick(*period) {
			start := time.Now()
			log.Infof("Running '%s' with argments %v", command, args)
			ctx, cancel := context.WithCancel(context.Background())
			cmd := exec.CommandContext(ctx, command, args...)
			result := make(chan pair)

			go func() {
				out, err := cmd.CombinedOutput()
				result <- pair{out, err}
			}()

			var out []byte
			var err error
			select {
			case pair := <-result:
				out = pair.out
				err = pair.err
			case <-time.After(*timeout):
				out = []byte("command timed out")
				err = fmt.Errorf("command timed out")
				cancel()
			}

			duration := time.Now().Sub(start)
			commandDuration.Observe(duration.Seconds())

			withLock(func() {
				lastRunStart = start
				lastRunDuration = duration
				outputBuf = out
			})

			reap()

			if err != nil {
				if exiterr, ok := err.(*exec.ExitError); ok {
					if status, ok := exiterr.Sys().(syscall.WaitStatus); ok {
						code := status.ExitStatus()
						log.Infof("Command exited with code: %d", code)
						statusCode.Set(float64(code))
						continue
					}
				}
				log.Warnf("Error running command: %v", err)
				log.Printf("Output:\n%s", out)
				statusCode.Set(255)
				continue
			}

			log.Printf("Command exited successfully")
			statusCode.Set(0)
		}
	}()

	tmpl, err := template.New("index").Parse(`<html>
	<head><title>Prometheus Command Runner</title></head>
	<body>
	  <h2>Prometheus Command Runner</h2>
	  <p>"{{.Command}}" output:</p>
	  <pre>{{.Output}}</pre>
	  <p>Run at {{.Time}} took {{.Duration}}<p>
	</body>
	</html>`)
	if err != nil {
		log.Fatalf("Failed to parse template: %v", err)
	}

	prometheus.MustRegister(statusCode)
	prometheus.MustRegister(commandDuration)
	http.Handle("/", http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		withLock(func() {
			tmpl.Execute(w, struct {
				Command, Output string
				Time            time.Time
				Duration        time.Duration
			}{
				Command:  command + " " + strings.Join(args, " "),
				Output:   string(outputBuf),
				Time:     lastRunStart,
				Duration: lastRunDuration,
			})
		})
	}))
	http.Handle("/metrics", prometheus.Handler())

	log.Printf("Listening on address %s", *listenAddr)
	http.ListenAndServe(*listenAddr, nil)
}
