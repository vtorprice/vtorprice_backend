find . -path "*/migrations/*.py" -not -name "__init__.py"  -delete &&
find . -path "*/__pycache__/*.pyc"  -delete &&
find . -path "*/__pycache__"  -delete &&

echo "OK"