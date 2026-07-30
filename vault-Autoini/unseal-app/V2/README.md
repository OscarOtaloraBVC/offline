## Version:
Version funcional de aplicaion de unseal sin persistencia.

tener en cuenta uqe se compila desde linux

find . -type f -exec dos2unix {} +

compilado con:

docker build --no-cache -t localhost:5000/vault-autoini-front-v1:1.0 .
docker build --no-cache -t localhost:5000/vault-autoini-back-v1:1.0 .