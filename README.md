# schoology-automated-export
Automated Schoology IMSCC Full Course Export

1. Create a transfer-schoolname-# (ex. transfer-riverdale-1) with the proper rights to view and edit all Schoology courses
2. Get Section Export from Schoology as a CSV file for the academic year you want to export (CSV format in the project here)
3. Configure script settings for the school year (file names) and download location (recommend an external hard drive)
4. Configure a virtual python environment in whatever directory you are creating this project
5. Install the requirements.txt files in your virtual environment
6. Run the script in MODE=1 for the staging (saving to resources, and then "exporing" to File Transfer). This is all the steps BEFORE the download.
7. Run the script in MODE=2 for the downloading (saving IMSCC files with naming convention to save location)
