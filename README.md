<img align="right" alt="ORCA logo" title="ORCA logo" src="https://github.com/Apexal/orca/blob/master/assets/logo.png?raw=true" width="300">

### **ORCA** is an open-source API for RPI's course schedule.

Deployed at [https://rcos-orca.herokuapp.com/docs](https://rcos-orca.herokuapp.com/docs) [(alternate docs)](https://rcos-orca.herokuapp.com/redoc)

## Overview
ORCA gives you access to every course offered in a semester along with the sections scheduled with weekly periods. This includes:
- course title
- course id (e.g. BIOL-1010)
- course sections with
    - crn
    - id (section 01, 02, ...)
    - how many credits it can be taken for
    - current enrollment count
    - max enrollment count
    - url to textbooks (RPI Bookstore)
    - section periods with
        - type (lecture, recitation, lab, ...)
        - start and end time
        - days of the week it meets
        - instructor(s)
        - location

Look at the requests' example responses to see the full schemas.

### Data
ORCA periodically fetches its data from the SIS page listing course sections with enrollment data in table format. [Spring 2021 Example](https://sis.rpi.edu/reg/zs202101.htm)
The page is extremely difficult to read and is even difficult to programmatically parse. These pages are fetched every **30 minutes** each day, though it is unclear how often the Registrar updates the pages themselves.

![Prod Auto Update](https://github.com/Apexal/orca/workflows/Prod%20Auto%20Update/badge.svg)

### Uses
This course data can be used for a variety of purposes small and large. Here are some examples:
- create your own scheduling interface (e.g. YACS or QuACS)
- create student tools that use course data
    - used textbook marketplace
    - study group organizers
    - schedule visualizers
    - schedule importers
- data visualizations
    - map out locations of periods
    - create directions for getting to and from classes

### Documentation

#### Semesters
The Registrar evidently identifies semesters with a short numeric code comprising:
1. 4-digit year the semester starts during
2. 2-digit zero padded month the semester starts during
3. (Arch) 2-digit code for specific part of semester
    - `01` - Full Term
    - `02` - First Half
    - `03` - Seond Half

**Examples**
- `20210` Spring 2021
- `202009` Fall 2020
- `20210501` Summer 2021 (Full Term)

#### Database Schema
[Here](https://dbdiagram.io/d/5fbb43a63a78976d7b7cfb03) is a visualization of the simple database schema used for the API. It also has the schema written in Database Markup Language.


#### Source Code
ORCA is entirely open source and hosted on GitHub at [Apexa/orca](https://github.com/Apexal/orca)

### Issues/Feature Requests

Please report these on the GitHub repo at [Apexa/orca](https://github.com/Apexal/orca/issues)!

### Main Contributors

- Frank Matranga ([@Apexal](https://github.com/Apexal))
- Joshua Wu ([@123joshuawu](https://github.com/123joshuawu))