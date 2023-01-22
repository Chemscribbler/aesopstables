# WIP on Reimplementing what became [Aesop's Tables](https://github.com/Chemscribbler/sass)

Ultimate goal is to have a super easy to deploy (heroku or heroku like)

## Getting Started:

This project includes a Dockerfile for ease of development, but can also be run locally on your machine if you'd like.

### Docker

To run the application using Docker you will first need to download [Docker](https://www.docker.com/), which is a free software to increase application portability. Once you have docker installed, launch it and run the following command from the root of the project reop:

```
docker build --tag aesops .
```

This will "build" the docker image, and add it to your local registry of docker images. You can then launch the application with the following command:

```
docker run -d -p 5000:5000 aesops
```

This will serve the application at [`http://localhost:5000/`](http://localhost:5000/).

Each time you make changes to the application, you will need to re-build the image to roll in the latest version of the code.

### Local

install requirements using `pip install -r requirements.text`

then run:
`flask db init`
`flask db migrate`
`flask db upgrade`

and then to interface with an environment where the datatables are pre-loaded you can use
`flask shell`

You will still need to import utility functions

