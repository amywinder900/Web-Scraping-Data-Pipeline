FROM python:3.8

RUN \
    #adds keys to apt for repositories
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \ 
    #adds google chrome
    &&  sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get -y update && apt-get install -y google-chrome-stable \
    #downloads chromedriver
    && wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS \
        chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip \
    && apt-get install -yqq unzip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
COPY . . 
RUN pip install -r requirements.txt
ENTRYPOINT ["python3", "scraper_prototype/scraper_prototype.py"]