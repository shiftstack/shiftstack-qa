# Purpose

Role to run day2ops procedures, confirming that the cluster remains operative by
running the verification role afterwards.

It automatically creates a must-gather in case of failure.

# Configuration

User should call this role passing a variable called `day2ops_steps`.

This variable is a list of procedures to run. The order inside the list is considered.
If the variable is not passed, the role will fail.

Before running the procedure the role will check if the procedure is defined inside
the procedure directory with the extension `.yml`. If it does not exist, the role will fail.

# How to add a new day2ops procedure

You just need to create a file inside the `tasks/procedure` directory with the name of the procedure.
The name of the file without the extension is the keywork that should be added as element in the var `day2ops_steps` to trigger the execution of the procedure while running this role.