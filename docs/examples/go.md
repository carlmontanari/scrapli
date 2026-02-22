# Go

This page contains a very simple example for using scrapli to connect to a CLI device (telnet/ssh) as well as a NETCONF server -- there are many more examples [here](https://github.com/scrapli/scrapligo/tree/main/examples), so check those out too.


## CLI


```go
package main

import (
	"context"
	"fmt"
	"time"

	scrapligocli "github.com/scrapli/scrapligo/cli" // (1)
	scrapligooptions "github.com/scrapli/scrapligo/options" // (2)
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second) // (3)
	defer cancel()

	opts := []scrapligooptions.Option{ // (4)
		scrapligooptions.WithDefintionFileOrName(scrapligocli.NokiaSrlinux),
		scrapligooptions.WithUsername("scrapli"),
		scrapligooptions.WithPassword("verysecurepassword"),
	}

	c, err := scrapligocli.NewCli( // (5)
		"myrouter",
		opts...,
	)
	if err != nil {
		panic(fmt.Sprintf("failed creating cli object, error: %v", err))
	}

	_, err = c.Open(ctx) // (6)
	if err != nil {
		panic(err)
	}

	defer c.Close(ctx) // (7)

	r, err := c.SendInput(ctx, "info") // (8)
	if err != nil {
		panic(err)
	}

	fmt.Println(r.Result()) // (9)
}
```

1. The `cli` package of course holds cli related things, including the `NewCli` function we'll use a bit later.
2. We'll also import the `options` package -- this holds all the options we'll use when establishing our connection.
3. Rejoice gophers! scrapligo uses context cancellation like you'd expect any go package to do (this was historically not the case).
4. Here we create a slice of options to pass to the `NewCli` function -- in this example we are setting the definition to use the `NokiaSrlinux` definition, and setting a dummy username/password.
5. And now we can create our `Cli` object with our given options to connect to "myrouter" in this case.
6. Now we can open the connection using the appropriately named `Open` method.
7. Always make sure to defer closing the connection -- this is especially important for daemons/long running programs as the `Close` method is where resources will be freed.
8. We can use `SendInput` to... send an input to the device...
9. Finally, we can access the full output from the result using the `Result()` method of the `Result` object that we got returned from `SendInput`.


## NETCONF


```go
package main

import (
	"context"
	"fmt"
	"time"

	scrapligonetconf "github.com/scrapli/scrapligo/netconf" // (1)
	scrapligooptions "github.com/scrapli/scrapligo/options" // (2)
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second) // (3)
	defer cancel()

	opts := []scrapligooptions.Option{ // (4)
		scrapligooptions.WithUsername("scrapli"),
		scrapligooptions.WithPassword("verysecurepassword"),
	}

	n, err := scrapligonetconf.NewNetconf( // (5)
		"myrouter",
		opts...,
	)
	if err != nil {
		panic(fmt.Sprintf("failed creating netconf object, error: %v", err))
	}

	_, err = n.Open(ctx) // (6)
	if err != nil {
		panic(err)
	}

	defer n.Close(ctx) // (7)

	r, err := n.GetConfig(ctx) // (8)
	if err != nil {
		panic(err)
	}

	fmt.Println(r.Result()) // (9)
}
```

1. The `netconf` package of course holds NETCONF related things, including the `NewNetconf` function we'll use a bit later.
2. We'll also import the `options` package -- this holds all the options we'll use when establishing our connection -- same as with the CLI example.
3. Again, normal context things here.
4. Here we create a slice of options to pass to the `NewNetconf` function -- in this example we are just setting a dummy username/password.
5. And now we can create our `Netconf` object with our given options to connect to "myrouter" in this case.
6. Now we can open the connection using the appropriately named `Open` method.
7. Always make sure to defer closing the connection -- this is especially important for daemons/long running programs as the `Close` method is where resources will be freed.
8. We can use `GetConfig` to... send a get-config rpc to the device...
9. Finally, we can access the full output from the result using the `Result()` method of the `Result` object that we got returned from `GetConfig`.
