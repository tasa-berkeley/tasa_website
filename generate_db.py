from tasa_website import init_db

print 'Are you sure you want init the db?'
print 'This will overwrite any existing database.'
print 'Enter yes to confirm'

res = str(raw_input())
if res == 'yes':
    init_db()
    print 'Database generated'
