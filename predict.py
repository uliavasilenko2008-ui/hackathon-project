import sys
import json
from data_loader import read_jsonl
from schemas import IncomingTicket, build_response

src, dst = sys.argv[1], sys.argv[2]
with open(dst, "w", encoding="utf-8") as out:
    for raw in read_jsonl(src):
        row = build_response(IncomingTicket(**raw)).model_dump()
        row["ticket_id"] = raw.get("ticket_id")
        out.write(json.dumps(row, ensure_ascii=False) + "\n")