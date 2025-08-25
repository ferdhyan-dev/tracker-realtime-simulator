INSERT INTO vehicles (vehicle_id, name, type, plate_no, capacity, owner) VALUES
 ('vhc01','Truck 01','truck','B 1234 XX',18.0,'PT Demo Logistics'),
 ('SHIP01','Sun Flower','passenger','IMO1234567',500,'OAR')
ON CONFLICT (vehicle_id) DO NOTHING;

-- contoh 1 titik awal (boleh dihapus jika pakai simulator)
INSERT INTO positions (vehicle_id, lat, lon, sog, cog, heading, status, ts) VALUES
 ('vhc01', -6.2000, 106.8167, 40, 90, 90, 'Moving', NOW());
