pipinstall:
	python3 -m pip install update pip
	python3 -m pip install --upgrade pip
	python3 -m pip install -r ./requirements.txt

build:
	sudo docker build --no-cache --network=host -t tg-bot .

run:
