def pdf2text(filename):
    from tika import parser
    raw = parser.from_file(filename + '.pdf')

    f = open(filename + '.txt', 'w+')
    f.write(raw['content'].strip())
    f.close

import sys
pg_name = sys.argv[0]
args = sys.argv[1:]

if len(sys.argv) != 2:
    print("Usage: ", pg_name)
    print("Please specify One argument")
    sys.exit(1)

pdf2text(args[0])