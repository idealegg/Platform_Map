#!/usr/bin/expect
spawn ssh -l system jnsev01v011
set timeout 3
set done 1
set nologined 1
set timeout_case 0

while ($done) {
  expect {
    " login:" { if ($nologined) {
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
          send "\n"
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
              if ($timeout_case < 0) {
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