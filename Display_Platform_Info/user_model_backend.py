from django.contrib.auth.backends import ModelBackend
from models import User


class UserModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        #print "UserModelBackend.authenticate"
        try:
            user = User.objects.get(username=username)
        except:
            try:
                user = User.objects.get(mobile=username)
            except:
                try:
                    user = User.objects.get(email=username)
                except:
                    return None
        #print "user: %s, passwd: %s in db!" % (user.username, user.password)
        #print "user: %s, passwd: %s input!" % (username, password)
        if user.check_password(password):
            #print "check_password yes"
            return user
        else:
            #print "check_password no"
            return None
