[app]
title = ToDoStudy
package.name = todostudy
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,sqlite3
orientation = portrait
osx.kivy_version = 2.2.1
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
[buildozer]
# ...existing config...

[app:app]
# ...existing config...

[buildozer]
# ...

[buildozer:buildozer]
python_version = 3.11
# or use python_version = 3.10 for even better compatibility
