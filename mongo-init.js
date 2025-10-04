
db = db.getSiblingDB('openf1');

db.createUser({
  user: 'f1admin',
  pwd: 'Supersecret1',
  roles: [
    {
      role: 'readWrite',
      db: 'openf1'
    }
  ]
});


db.createCollection('sessions');
db.createCollection('drivers');
db.createCollection('laps');
db.createCollection('car_data');
db.createCollection('positions');
db.createCollection('intervals');

print('Database initialized successfully');