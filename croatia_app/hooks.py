app_name = "croatia_app"
app_title = "računovodstvo Hrvatska"
app_publisher = "Logicna Podloga J.d.o.o"
app_description = "računovodstvo for croatia"
app_email = "gjorgji.mladenovski@logicna-podloga.com"
app_license = "gpl-3.0"

# Apps
# ------------------

required_apps = ["erpnext"]

# Translation
# ------------------
translations = [
    {
        "source_name": "croatia_app/translations/hr.po",
        "target_name": "croatia_app/translations/hr-target.po"
    }
]

# After install
after_install = "croatia_app.setup.after_install"

# Rest of the hooks.py remains unchanged...
