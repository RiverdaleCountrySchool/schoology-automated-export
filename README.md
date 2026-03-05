# schoology-automated-export
Making of the Program:

1. I recorded all the clicks and steps necessary to export a single course from Schoology as an IMSCC file
2. Using those steps, consolidated in a single file (example in this directory), I used Gemini CLI to create the script

Automated Schoology IMSCC Full Course Export

1. Create a generic account on your Schoology instance (ex. mySchoolTest-1) with the proper rights to view and edit all Schoology courses
2. Based on our testing, create new generic accounts for different export years/groups. It's much easier than "bulk deleting" from Transfer History OR Resources :)
3. Get Section Export from Schoology as a CSV file for the academic year you want to export (CSV format in the project here)
4. Configure script settings for the school year (file names) and download location (recommend an external hard drive)
5. Configure a virtual python environment in whatever directory you are creating this project
6. Install the requirements.txt pip libraries in your virtual environment
7. Run the script in MODE=1 for the staging (saving to resources, and then "exporing" to File Transfer). This is all the steps BEFORE the download.
8. In the Chromium window from Playwright, sign into your Schoology instance
9. Click resume once your Playwright Chromium instance is logged in with the proper scope
10. Run the script in MODE=2 for the downloading (saving IMSCC files with naming convention to save location)
11. In the Chromium window from Playwright, sign into your Schoology instance
12. Click resume once your Playwright Chromium instance is logged in with the proper scope

Note: you WILL need to change the URL template strings depending on how your Schoology instance is configured. Hopefully the script makes that clear :)

