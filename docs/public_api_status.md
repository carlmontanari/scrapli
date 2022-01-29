# Public API Status

Note that all public methods, unless otherwise noted, are available in sync and async form depending on the driver
 you have selected.


## Drivers

### Driver

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| open                          | 2020.03.29  |             |                                                              |
| close                         | 2020.03.29  |             |                                                              |
| isalive                       | 2020.03.29  |             |                                                              |


### AsyncDriver

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| open                          | 2020.06.06  |             |                                                              |
| close                         | 2020.06.06  |             |                                                              |
| isalive                       | 2020.06.06  |             |                                                              |


### GenericDriver (and NetworkDriver sub-classes unless overridden)

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| get_prompt                    | 2020.03.29  |             |                                                              |
| send_command                  | 2020.03.29  | 2020.08.09  | added `timeout_ops` keyword argument to modify timeout       |
| send_commands                 | 2020.03.29  | 2020.12.31  | added `eager` keyword argument                               |
| send_commands_from_file       | 2020.04.30  | 2020.12.31  | added `eager` keyword argument                               |
| send_interactive              | 2020.03.29  | 2021.01.30  | added `interaction_complete_patterns` keyword argument       |
| send_and_read                 | 2020.08.28  |             |                                                              |
| send_callback                 | 2022.01.30  |             |                                                              |


### AsyncGenericDriver (and NetworkDriver sub-classes unless overridden)

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| get_prompt                    | 2020.06.06  |             |                                                              |
| send_command                  | 2020.06.06  | 2020.08.09  | added `timeout_ops` keyword argument to modify timeout       |
| send_commands                 | 2020.06.06  | 2020.12.31  | added `eager` keyword argument                               |
| send_commands_from_file       | 2020.06.06  | 2020.12.31  | added `eager` keyword argument                               |
| send_interactive              | 2020.06.06  | 2021.01.30  | added `interaction_complete_patterns` keyword argument       |
| send_and_read                 | 2020.08.28  |             |                                                              |
| send_callback                 | 2022.01.30  |             |                                                              |


### NetworkDriver (and Platform driver sub-classes unless overridden)

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| update_privilege_levels       | 2020.05.09  |             | update priv map/all prompt pattern if adding/modifying privs |
| acquire_priv                  | 2020.03.29  |             |                                                              |
| register_configuration_session| 2020.05.09  |             | register a config session so the priv level can be tracked   |
| send_config                   | 2020.05.09  | 2020.12.31  | added `eager` keyword argument                               |
| send_configs                  | 2020.03.29  | 2020.12.31  | added `eager` keyword argument                               |
| send_configs_from_file        | 2020.04.30  | 2020.12.31  | added `eager` keyword argument                               |
| send_interactive              | 2020.03.29  | 2021.01.30  | added `interaction_complete_patterns` keyword argument       |


### AsyncNetworkDriver (and Platform driver sub-classes unless overridden)

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| update_privilege_levels       | 2020.06.06  |             |                                                              |
| acquire_priv                  | 2020.06.06  |             |                                                              |
| register_configuration_session| 2020.06.06  |             |                                                              |
| send_config                   | 2020.06.06  | 2020.12.31  | added `eager` keyword argument                               |
| send_configs                  | 2020.06.06  | 2020.12.31  | added `eager` keyword argument                               |
| send_configs_from_file        | 2020.06.06  | 2020.12.31  | added `eager` keyword argument                               |
| send_interactive              | 2020.06.06  | 2021.01.30  | added `interaction_complete_patterns` keyword argument       |


## Channel

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| get_prompt                    | 2020.03.29  |             |                                                              |
| send_input                    | 2020.03.29  | 2020.12.31  | added `eager` keyword argument                               |
| send_inputs_interact          | 2020.03.29  | 2020.04.11  | changed to support list of "events" to interact with         |
| send_input_and_read           | 2020.08.28  |             |                                                              |


## AsyncChannel

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| get_prompt                    | 2020.06.06  |             |                                                              |
| send_input                    | 2020.06.06  | 2020.12.31  | added `eager` keyword argument                               |
| send_inputs_interact          | 2020.06.06  |             |                                                              |
| send_input_and_read           | 2020.08.28  |             |                                                              |


## Transport

### Transport ABC (and Transport sub-classes unless overridden)

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| open                          | 2020.03.29  |             |                                                              |
| close                         | 2020.03.29  |             |                                                              |
| isalive                       | 2020.03.29  |             |                                                              |
| read                          | 2020.03.29  |             |                                                              |
| write                         | 2020.03.29  |             |                                                              |
| set_timeout                   | 2020.03.29  |             |                                                              |


### AsyncTransport ABC (and Transport sub-classes unless overridden)

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| open                          | 2020.06.06  |             |                                                              |
| close                         | 2020.06.06  |             |                                                              |
| isalive                       | 2020.06.06  |             |                                                              |
| read                          | 2020.06.06  |             |                                                              |
| write                         | 2020.06.06  |             |                                                              |
| set_timeout                   | 2020.06.06  |             |                                                              |


## Response

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| genie_parse_output            | 2020.03.29  |             |                                                              |
| textfsm_parse_output          | 2020.03.29  |             |                                                              |
| ttp_parse_output              | 2020.10.10  |             | Unlike other parse methods, requires a template argument     |
| raise_for_status              | 2020.05.09  |             |                                                              |


## MultiResponse

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| raise_for_status              | 2020.05.09  |             |                                                              |


## SSHConfig

| Method                        | Implemented | Last Change | Notes                                                        |
|-------------------------------|-------------|-------------|--------------------------------------------------------------|
| lookup                        | 2020.03.29  |             |                                                              |
