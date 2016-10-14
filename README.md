# Secure Tours

Landing page whilst the website is under construction.

## Setup

The contents of the `src` folder will be served by a simple [nginx](https://nginx.org/) [Docker](https://www.docker.com/) container.

To alter the website replace the contents of the `src` folder, build the container, and test.

## Build the container

To produce a Docker container suitable to serve the site, issue the following command.

    docker build -t goodtune/securetours .

## Run the container

To start the container issue the following command to run it in the foreground on port 80.

    docker run --rm -it --publish 80:80 goodtune/securetours

You can now visit http://localhost/ in your web browser to test the container.

## Ship the container

1. Use `git` to commit your changes and push the back to GitHub.
2. Create a pull-request (PR) to have your changes included in the official build.

Once the PR is merged, Docker Hub will automatically build a new container that can be deployed to production.
