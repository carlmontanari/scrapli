package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"crypto/rsa"
	"errors"
	"fmt"
	"log"
	mathrand "math/rand"
	"net"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"

	"golang.org/x/crypto/ssh"
)

const versionOutput = `Cisco IOS Software, C3560CX Software (C3560CX-UNIVERSALK9-M), Version 15.2(4)E7, RELEASE SOFTWARE (fc2)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2018 by Cisco Systems, Inc.
Compiled Tue 18-Sep-18 13:20 by prod_rel_team

ROM: Bootstrap program is C3560CX boot loader
BOOTLDR: C3560CX Boot Loader (C3560CX-HBOOT-M) Version 15.2(4r)E5, RELEASE SOFTWARE (fc4)

C3560CX uptime is 4 weeks, 6 days, 17 hours, 27 minutes
System returned to ROM by power-on
System restarted at 15:32:45 PDT Sun May 24 2026
System image file is "flash:c3560cx-universalk9-mz.152-4.E7.bin"
Last reload reason: power-on



This product contains cryptographic features and is subject to United
States and local country laws governing import, export, transfer and
use. Delivery of Cisco cryptographic products does not imply
third-party authority to import, export, distribute or use encryption.
Importers, exporters, distributors and users are responsible for
compliance with U.S. and local country laws. By using this product you
agree to comply with applicable laws and regulations. If you are unable
to comply with U.S. and local laws, return this product immediately.

A summary of U.S. laws governing Cisco cryptographic products may be found at:
http://www.cisco.com/wwl/export/crypto/tool/stqrg.html

If you require further assistance please contact us by sending email to
export@cisco.com.

License Level: ipservices
License Type: Permanent Right-To-Use
Next reload license Level: ipservices

cisco WS-C3560CX-8PC-S (APM86XXX) processor (revision A0) with 524288K bytes of memory.
Processor board ID XXXXXXXXXXX
Last reset from power-on
3 Virtual Ethernet interfaces
12 Gigabit Ethernet interfaces
The password-recovery mechanism is enabled.

512K bytes of flash-simulated non-volatile configuration memory.
Base ethernet MAC Address       : XX:XX:XX:XX:XX:XX
Motherboard assembly number     : XX-XXXXX-XX
Power supply part number        : XXX-XXXX-XX
Motherboard serial number       : XXXXXXXXXXX
Power supply serial number      : XXXXXXXXXXX
Model revision number           : A0
Motherboard revision number     : A0
Model number                    : WS-C3560CX-8PC-S
System serial number            : XXXXXXXXXXX
Top Assembly Part Number        : XX-XXXX-XX
Top Assembly Revision Number    : A0
Version ID                      : V01
CLEI Code Number                : XXXXXXXXXX
Hardware Board Revision Number  : 0x02


Switch Ports Model                     SW Version            SW Image
------ ----- -----                     ----------            ----------
*    1 12    WS-C3560CX-8PC-S          15.2(4)E7             C3560CX-UNIVERSALK9-M


Configuration register is 0xF`

var onlyOneSignalHandler = make(chan struct{}) //nolint: gochecknoglobals

func main() {
	ctx, cancel := signalHandledContext(fmt.Printf) //nolint: forbidigo
	defer cancel()

	sshConfig := &ssh.ServerConfig{
		PasswordCallback: func(c ssh.ConnMetadata, pass []byte) (*ssh.Permissions, error) {
			if c.User() == "admin" && string(pass) == "password" {
				return nil, nil
			}

			return nil, fmt.Errorf("creds are admin/password only")
		},
	}

	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		panic(err)
	}

	signer, err := ssh.NewSignerFromKey(privateKey)
	if err != nil {
		panic(err)
	}

	sshConfig.AddHostKey(signer)

	listenConfig := &net.ListenConfig{
		Control: func(_, _ string, c syscall.RawConn) error {
			return nil
		},
	}

	listener, err := listenConfig.Listen(ctx, "tcp", "0.0.0.0:2222")
	if err != nil {
		panic(err)
	}

	fmt.Println("dumbo is listening...")

	var wg sync.WaitGroup

	go func() {
		<-ctx.Done()
		_ = listener.Close()
	}()

	for {
		conn, err := listener.Accept()
		if err != nil {
			if errors.Is(err, net.ErrClosed) {
				break
			}

			panic(err)
		}

		wg.Add(1)
		go func(conn net.Conn) {
			defer wg.Done()
			defer conn.Close()

			handleConnection(conn, sshConfig)
		}(conn)
	}

	wg.Wait()
}

func handleConnection(nConn net.Conn, config *ssh.ServerConfig) {
	_, chans, reqs, err := ssh.NewServerConn(nConn, config)
	if err != nil {
		log.Printf("handshake failed: %v", err)

		return
	}

	go ssh.DiscardRequests(reqs)

	for newChannel := range chans {
		if newChannel.ChannelType() != "session" {
			newChannel.Reject(ssh.UnknownChannelType, "unknown channel type")

			continue
		}

		channel, requests, err := newChannel.Accept()
		if err != nil {
			log.Printf("accept channel failed: %v", err)

			return
		}

		go handleChannel(channel, requests)
	}
}

func handleChannel(channel ssh.Channel, requests <-chan *ssh.Request) {
	defer channel.Close()

	go func() {
		for req := range requests {
			// we dont care, we are dumb
			req.Reply(true, nil)
		}
	}()

	// write a prompt we can find to know we got authenticated
	_, _ = channel.Write([]byte("router> "))

	var input bytes.Buffer

	buf := make([]byte, 1024)

	for {
		n, err := channel.Read(buf)
		if err != nil {
			break
		}

		input.Write(buf[:n])

		if n == 0 {
			continue
		}

		// echo input back on the hcannel
		_, err = channel.Write(buf[:n])
		if err != nil {
			break
		}

		if !(bytes.Contains(input.Bytes(), []byte("\r")) ||
			bytes.Contains(input.Bytes(), []byte("\n"))) {
			continue
		}

		if bytes.Contains(input.Bytes(), []byte("show version")) {
			time.Sleep(time.Duration(mathrand.Intn(500)) * time.Millisecond)

			_, err = channel.Write([]byte(strings.ReplaceAll(versionOutput, "\n", "\r\n")))
			if err != nil {
				break
			}
		} else if bytes.Contains(input.Bytes(), []byte("exit")) {
			break
		}

		input = bytes.Buffer{}

		_, err = channel.Write([]byte("\r\nrouter> "))
		if err != nil {
			continue
		}
	}
}

func signalHandledContext(
	logf func(format string, a ...any) (n int, err error),
) (context.Context, context.CancelFunc) {
	// panics when called twice, this way there can only be one signal handled context
	close(onlyOneSignalHandler)

	ctx, cancel := context.WithCancel(context.Background())

	sigs := make(chan os.Signal, 2) //nolint:mnd

	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigs

		_, _ = logf("received signal '%s', canceling context", sig)

		cancel()

		<-sigs

		_, _ = logf("received signal '%s', exiting program", sig)

		os.Exit(1)
	}()

	return ctx, cancel
}
