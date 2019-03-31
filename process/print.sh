#!/bin/bash
set -euxo pipefail

BUCKET=stickers-submissions-352b2c6b-d476-4ab5-8f84-83d9f455ccf9
WORKDIR=$(mktemp -d)
function finish {
    rm -rf "$WORKDIR"
}
trap finish EXIT

for uuid in $(aws s3api list-objects-v2 --bucket "$BUCKET" --output text --query Contents[].Key | tr '\t' '\n' | grep -v '/'); do
    if aws s3api get-object-tagging --bucket "$BUCKET" --key "$uuid" --output text | grep -q 'validated[[:space:]]\+yep'; then
        aws s3api get-object --bucket "$BUCKET" --key "$uuid" "$WORKDIR/$uuid.json" >/dev/null
        aws s3 mv "s3://$BUCKET/$uuid" "s3://$BUCKET/done/$uuid" 1>&2
        jq -r '.address | join("\n")' "$WORKDIR/$uuid.json" | mapfile -t address
        sed <envelope-template.svg >"$WORKDIR/$uuid.svg" \
            -e "s^@@DATAMATRIX@@^data:image/png;base64,$(echo "$uuid" | tr -d '\n' | dmtxwrite -f PNG | base64 -w 0)^" \
            -e "s@@LINE1@@$(jq -r '.address[0]' "$WORKDIR/$uuid.json")" \
            -e "s@@LINE2@@$(jq -r '.address[1]' "$WORKDIR/$uuid.json")" \
            -e "s@@LINE3@@$(jq -r '.address[2]' "$WORKDIR/$uuid.json")" \
            -e "s@@LINE4@@$(jq -r '.address[3]' "$WORKDIR/$uuid.json")"
        inkscape -z -f "$WORKDIR/$uuid.svg" -A "$WORKDIR/$uuid.pdf"
    fi
done

pdfunite "$WORKDIR"/*.pdf "$WORKDIR/final.pdf"
cat "$WORKDIR/final.pdf"

>&2 echo "please make sure the duplexer is off <3"
