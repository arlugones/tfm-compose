FROM rstudio/plumber

RUN apt-get update && apt-get install -y \ 
	libpq-dev && \
	rm -rf /var/lib/apt/lists/*

RUN R -e "install.packages(c('dplyr', 'TAM', 'RPostgres', 'dotenv', 'readxl'), repos = 'https://cloud.r-project.org')"

WORKDIR /app

COPY api.R  .
COPY data/ data/

CMD ["/app/api.R"]
