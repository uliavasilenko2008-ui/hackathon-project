IN ?= data/tickets_valid.jsonl
OUT ?= pred.jsonl

predict:
	python predict.py $(IN) $(OUT)