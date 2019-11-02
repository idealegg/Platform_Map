#!/usr/bin/expect
set timeout 3
set done 1
set nologined 1
set timeout_case 0
spawn ssh -o ConnectTimeout=1 -l system whsev01v012
while (${done}) {
  expect {
    " login:" { if (${nologined}) {
                   send "system\n"
                   }
    }
    "Password:" { send "abc123\n"
                  set nologined 0
                  }
    "password:" { send "abc123\n"
                  set nologined 0
                  }
    "system@" {
          set done 0
expect "system@"
send "uname -a\n"
expect "system@"
send "cat /etc/thalix-release\n"
expect "system@"
send "ifconfig -a\n"
expect "system@"
send "vers\n"
expect "system@"
send "message\n"
expect "system@"
send "cat /etc/xinetd.d/x11-fw\n"
          expect "system@"
          send "exit\n"
          expect " login:"
          send_user "\n\nFinished...\n\n"
          
          exit
        }
        timeout {
              if (${timeout_case} < 0) {
                send "\n" }
              else{
                  puts stderr "Login time out...\n"
                  exit 1
              }
           incr timeout_case
         }
   }
}




exit 0