# EXL Hackathon 2022 ![HackerEarth](https://img.shields.io/badge/HackerEarth-%232C3454.svg?style=for-the-badge&logo=HackerEarth&logoColor=Blue) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)
## Cloud Agnostic Solution 
![Azure](https://img.shields.io/badge/azure-%230072C6.svg?style=for-the-badge&logo=microsoftazure&logoColor=white) ![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white) ![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)  ![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white) ![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white) ![Postman](https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white) ![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white) ![DigitalOcean](https://img.shields.io/badge/DigitalOcean-%230167ff.svg?style=for-the-badge&logo=digitalOcean&logoColor=white)

This is a cloud agnostic solution which works for AWS and Azure Cloud providers. This provides a set 
of API's, which a user can use to upload and download the files from cloud storages.

## Installation

User will require docker installed in his system to make the application up and running.
Postman is another dependancy, to test the RestAPI endpoints.

For creation of [![docker-compose](https://img.shields.io/badge/digitalocean-docker_compose.yml-blue?style=flat&logo=digitalocean)](https://www.digitalocean.com/community/tutorials/how-to-set-up-flask-with-mongodb-and-docker) 
<br>
I have used the open-source docs available on Digital-Ocean platform.

## Usage

1. Clone the git repo.
2. In the root folder of this git repo, run below commands.
```docker
$ docker-compose up -d
```
3. Once build is done, use below command to list the running containers:
```docker
$ docker ps
```

### `Create a User for MongoDB Database`
![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)

To do this, you will need the root username and password that you set in the docker-compose.yml file environment variables `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD` for the mongodb service.
It’s better to avoid using the root administrative account when interacting with the database.
Thus, I created a dedicated database user for my application.

!! `Steps to create user:`

```docker
$ docker exce -it mongodb bash
```
If user is on windows, he/she may use the [docker-desktop](https://docs.docker.com/desktop/windows/install/).

```docker
root:/# mongo -u admin -p
```
Enter password as `admin`.

### NOTE: 
the password that you entered as the value for the `MONGO_INITDB_ROOT_PASSWORD` variable in the `docker-compose.yml` file. 

Run this to list all databases:
```docker
mongodb> show dbs;
```

Execute the `use` command to switch to the `user_clouds` database:
```docker
mongodb> use user_clouds
```

Now create a new user that will be allowed to access this database:
```docker
mongodb> db.createUser({user: 'admin', pwd: 'admin', roles: [{role: 'readWrite', db: 'cloud_users'}]})
mongodb> exit
```

Log in to the authenticated database with the following command:
```docker
$ mongo -u admin -p admin --authenticationDatabase cloud_users
mongodb> exit
root:/# exit
```

## Test Application on `POSTMAN`
![Postman](https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white)

To test the restAPI endpoints\
use [home](http://127.0.0.1/). 
```
http://127.0.0.1/           # home url
```



## Supported Cloud Providers
![Azure](https://img.shields.io/badge/azure-%230072C6.svg?style=for-the-badge&logo=microsoftazure&logoColor=white) ![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)

Right now, only Azure and AWS is supported, but this can be extended using the `StorageAction` Class.

 |provider  |   keys|
 |:----------:|:-------:|
 |Azure (`az`)| 1. connection_string|
 |     | 2. bucket_name <br>(In azure cloud it is known as `container name`)|
 | AWS (`aws`)|1. access_key|
 |  |2. secret_access_key|
 |  |3. bucket_name   |
 |  |                   |

## restAPI Endpoints:

|API Endpoint | Method Type     | Parameters Accepted       |  Intented For |
|:-------------:|:-------------:|:--------------------:     |:---------------:|
|/upload-public|    POST    | 1.provider (`az, aws`)  <br> 2. file (file to be uploaded) <br>  3. Keys (as per `provider`, see `Supported Cloud providers table `) <br>    4. bucket_name     | Anonymous User              
|/view-public   |   POST    | Same as above                 | Anonymous User
|/delete        |   POST    |1. token (`header x-access-token`) <br> 2. filename     | Registered User 
|/all           |   POST    |1. token (`header x-access-token`) <br>| Registered
|/download      |   POST    |1. token (`header x-access-token`) <br> 2. filename| Registered User
|/upload        |   POST    |1. token (`header x-access-token`) <br> 2. file | Registered User
|/add           |   POST    |1.provider (`az, aws`) <br> 2. token (`header x-access-token`) <br> 3.Keys (as per `provider`, see `Supported Cloud providers table `)| Resigtered User
|/login         |   POST    | 1.email <br> 2. password <br> 3.provider (`az, aws`) |   Registered User can login
|/signup        |   POST    | 1. email <br> 2. password <br> 3. provider (`az, aws`) <br> 4. name| Any user can signup
|/              |   GET     |                           |   Any User can visit the home page
|               |           |                           |

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)