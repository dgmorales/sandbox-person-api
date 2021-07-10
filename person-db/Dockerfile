FROM mongo

EXPOSE 27017/tcp
ENV MONGO_INITDB_DATABASE=people

COPY ./initdb/* /docker-entrypoint-initdb.d/