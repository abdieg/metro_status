# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install necessary dependencies
RUN apt-get update && apt-get install -y wget unzip gnupg curl --no-install-recommends

# Select Chrome and Chromedriver version
# Check "https://googlechromelabs.github.io/chrome-for-testing/#stable" for availability
ARG CHROME_VERSION="134.0.6998.88"

# Install Chrome
RUN wget -O /tmp/chromebrowser.zip https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chrome-headless-shell-linux64.zip \
    && unzip -j /tmp/chromebrowser.zip "chrome-headless-shell-linux64/chrome-headless-shell" -d /usr/local/bin/ \
    && rm /tmp/chromebrowser.zip

# Install Chromedriver
RUN wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip \
    && unzip -j /tmp/chromedriver.zip "chromedriver-linux64/chromedriver" -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

#Install dependencies for chromedriver and chrome
RUN apt-get install -y chromium

# Run scrapper_lionbridge.py when the container launches
CMD ["python", "metro.py"]
