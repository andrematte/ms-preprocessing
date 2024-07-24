.DEFAULT_GOAL=help
INPUT_DIR = /Users/andrematte/Data/BVSA-test
OUTPUT_DIR = /Users/andrematte/Data/BVSA-test-output

help: # Show this help
	@egrep -h '\s#\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?# "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


setup: # Constroi a imagem do Docker
	@echo Building Docker Image...
	docker build -t ms-preprocessing:1.0.0 .


run: # Executa o pipeline de processamento das imagens contidas no diretorio INPUT_DIR, resultado é armazenado no diretorio OUTPUT_DIR
	@echo Executando processamento...
	docker run --rm \
	-p 8888:8888 \
	-u root \
	-v $(INPUT_DIR):/app/data/ \
	-v $(OUTPUT_DIR):/app/output/ \
	ms-preprocessing:1.0.0 \
	python micasense/batch_processing.py --imagepath ./data/ --outputpath ./output/ --panelpath ./data/BVSA-test/IMG_0000_1.tif