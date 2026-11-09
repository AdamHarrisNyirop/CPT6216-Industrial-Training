import json
import os

def build_profile(name, email):
  profile={"name":name,"email":email}
  unused_token = "temporary"
  print("Profile:",profile)
  return profile