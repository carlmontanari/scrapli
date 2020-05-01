# Public API Status

## Drivers

### Scrape

| Method                       | Implemented | Last Change | Notes                                                     |
|------------------------------|-------------|-------------|-----------------------------------------------------------|
| open                         | 2020.03.29  |             |                                                           |
| close                        | 2020.03.29  |             |                                                           |
| isalive                      | 2020.03.29  |             |                                                           |

### GenericDriver (and NetworkDriver sub-classes unless overridden)

| Method                       | Implemented | Last Change | Notes                                                     |
|------------------------------|-------------|-------------|-----------------------------------------------------------|
| get_prompt                   | 2020.03.29  |             |                                                           |
| send_command                 | 2020.03.29  |             |                                                           |
| send_commands                | 2020.03.29  |             |                                                           |
| send_commands_from_file      | 2020.04.30  |             |                                                           |
| send_interactive             | 2020.03.29  | 2020.04.11  | changed to support list of "events" to interact with      |


### NetworkDriver ABC (and Platform driver sub-classes unless overridden)

| Method                       | Implemented | Last Change | Notes                                                     |
|------------------------------|-------------|-------------|-----------------------------------------------------------|
| acquire_priv                 | 2020.03.29  |             |                                                           |
| send_command                 | 2020.03.29  |             |                                                           |
| send_commands                | 2020.03.29  |             |                                                           |
| send_commands_from_file      | 2020.04.30  |             |                                                           |
| send_configs                 | 2020.03.29  |             |                                                           |
| send_configs_from_file       | 2020.04.30  |             |                                                           |
                          

## Channel

| Method                       | Implemented | Last Change | Notes                                                    |
|------------------------------|-------------|-------------|----------------------------------------------------------|
| get_prompt                   | 2020.03.29  |             |                                                          |
| send_input                   | 2020.03.29  |             |                                                          |
| send_inputs_interact         | 2020.03.29  | 2020.04.11  | changed to support list of "events" to interact with     |


## Transport

### Transport ABC (and Transport sub-classes unless overridden)

| Method                       | Implemented | Last Change | Notes                                                   |
|------------------------------|-------------|-------------|---------------------------------------------------------|
| open                         | 2020.03.29  |             |                                                         |
| close                        | 2020.03.29  |             |                                                         |
| isalive                      | 2020.03.29  |             |                                                         |
| read                         | 2020.03.29  |             |                                                         |
| write                        | 2020.03.29  |             |                                                         |
| set_timeout                  | 2020.03.29  |             |                                                         |

### SystemSSHTransport

| Method                       | Implemented | Last Change | Notes                                                   |
|------------------------------|-------------|-------------|---------------------------------------------------------|
| open                         | 2020.03.29  |             |                                                         |
| isalive                      | 2020.03.29  |             |                                                         |
| set_timeout                  | 2020.03.29  |             |                                                         |

### TelnetTransport

| Method                       | Implemented | Last Change | Notes                                                   |
|------------------------------|-------------|-------------|---------------------------------------------------------|
| open                         | 2020.03.29  |             |                                                         |
| isalive                      | 2020.03.29  |             |                                                         |


## Response

| Method                       | Implemented | Last Change | Notes                                                   |
|------------------------------|-------------|-------------|---------------------------------------------------------|
| genie_parse_output           | 2020.03.29  |             |                                                         |
| textfsm_parse_output         | 2020.03.29  |             |                                                         |


## SSHConfig

| Method                       | Implemented | Last Change | Notes                                                   |
|------------------------------|-------------|-------------|---------------------------------------------------------|
| lookup                       | 2020.03.29  |             |                                                         |
