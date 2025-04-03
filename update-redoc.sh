if [ -z "$1" ]
  then
    echo "No version supplied"
    exit 1
fi

VER="$1"
DEST="./mkdocs_redoc_tag/redoc"
SOURCE="https://cdn.redoc.ly/redoc/$1/bundles/redoc.standalone.js"

# wget https://cdn.redoc.ly/redoc/v2.4.0/bundles/redoc.standalone.js
wget ${SOURCE} -O ${DEST}/javascripts/redoc.standalone.js
