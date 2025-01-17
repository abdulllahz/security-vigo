'GET https://payment1-loadboard.bykea.dev/v2/5e5766b05747d6e4fcbd1745/bookings?lat=24.8667398&lng=67.0808394&f_service_code=21&f_distance=5&sort=nearby'

headers: Joi.object({
    'x-lb-user-id': Joi.string().required(),
    'x-lb-user-token': Joi.string().required(),
    'lat': Joi.number().min(-90).max(90).optional(),
    'lng': Joi.number().min(-180).max(180).optional(),
}).options({ allowUnknown: true })

querystring: Joi.object({
    lat: Joi.number().min(-90).max(90).optional(),
    lng: Joi.number().min(-180).max(180).optional(),
    f_distance: Joi.number().positive().default(10),
    f_service_code: Joi.array().items(Joi.number()).optional().single(), // should be sent like: "f_service_code=21&f_service_code=22"
    sort: Joi.string().valid('nearby').default('nearby'),
    skip: Joi.number().positive().default(0),
    limit: Joi.number().positive().default(this.config.get("server:jobs:limit") || 14)
}).options({ allowUnknown: false })

const object = {..._querystring, ..._headers}
// B' = A U B

if(_.isNil(object.lat) || _.isNil(object.lng) ){
    throw boom.badRequest("Fields lat & lng are mandatory.");
}

const location = {
    lat: object.lat,
    lng: object.lng
};

const pagination = {
    skip: _querystring.skip,
    limit: _querystring.limit
};

const filters = {
    pickup_zone: _querystring.f_pickup_zone,
    dropoff_zone: _querystring.f_dropoff_zone,
    service_code: _querystring.f_service_code,
    amount_max,
    amount_min: _.get(session, 'partner_category_id.booking_fleet_threshold_min', 1),
    distance:  _.get(session, 'partner_category_id.booking_radius', di.cradle.config.get('server:distance_in_km')),
    session_partner: partner_id,
    radius_querystring
};



`Select ST_DistanceSphere(pickup_geom, 'POINT(${location.lng} ${location.lat})')/ 1000 as distance, ${selectColumns} from ${table} where `
`(case when amount is not NULL then amount >= 0 and ${fareThreshold} <= ${filters.amount_max} ELSE true END and `
`case when bid_amount is null then not exists (SELECT distinct bs.booking_id FROM bookings_sessions bs WHERE bs.partner_id = '${filters.session_partner}' and bs.booking_id = bookings.id) ELSE `
`not exists (SELECT distinct bs.booking_id FROM bookings_states bs WHERE bs.actor_id = '${filters.session_partner}' and bs.action='DRIVER_CANCELLED' and bs.actor_type='driver' and bs.booking_id = bookings.id) END  `
`and service_code in (${filters.service_code})) ${other_conditions}  and state='open'  and (`
`ST_DistanceSphere(pickup_geom, ST_GeomFromText('POINT(${location.lng} ${location.lat})',4326))/ 1000 < ${item.radius / 1000}`
`and CURRENT_TIMESTAMP <= dt + interval '${item.time_max.replace('s', '')} seconds' `
`and CURRENT_TIMESTAMP >= dt + interval '${item.time_min.replace('s', '')} seconds' `
') ORDER BY distance asc , case when bid_amount IS Not NULL then bid_amount end DESC '
await db.primary.query(`${query} (${_conditions}) ${orderBy} limit ${pagination.limit}`, { ...filters, ...location });
//Params===================================================================================================================================
location.lng, location.lat, fareThreshold, filters.amount_max, filters.session_partner, filters.service_code, other_conditions,
item.radius/1000, item.time_max.replace('s', ''), item.time_min.replace('s', ''), pagination.limit
//User Controlled Params===================================================================================================================
location.lng, location.lat, filters.service_code, pagination.limit
//Params Source============================================================================================================================
//location.lng_________|_querystring(Joi.number().min(-90).max(90).optional())/object/location/lng
//                     |_headers    (Joi.number().min(-90).max(90).optional())/object/location/lng

//location.lat_________|_querystring(Joi.number().min(-90).max(90).optional())/object/location/lat
//                     |_headers    (Joi.number().min(-90).max(90).optional())/object/location/lat 

//filters.service_code_|_querystring(Joi.array().items(Joi.number()).optional().single())/filters/service_code

//pagination.limit_____|_querystring(Joi.number().positive().default(this.config.get("server:jobs:limit") || 14)/pagination/limit


await db.primary.query(`${query} (${_conditions}) ${orderBy} limit ${pagination.limit}`, { ...filters, ...location });
// Example query:
// Select ST_DistanceSphere(pickup_geom, 'POINT(67.080777 24.8667537)')/ 1000 as distance, id,fare_est,trip_id,trip_type,trips,creator_type,pickup_address,pickup_lat,pickup_lng,dropoff_address,pickup_zone_ur,dropoff_zone_ur,dropoff_lat,dropoff_lng,service_code,rules,bid_amount,dt,is_fare_updated from bookings where (case when amount is not NULL then amount >= 0 and (amount + fare_est::INTEGER) <= 105124 ELSE true END and case when bid_amount is null then not exists (SELECT distinct bs.booking_id FROM bookings_sessions bs WHERE bs.partner_id = '6149c8d058394e0237d05529' and bs.booking_id = bookings.id) ELSE  not exists (SELECT distinct bs.booking_id FROM bookings_states bs WHERE bs.actor_id = '6149c8d058394e0237d05529' and bs.action='DRIVER_CANCELLED' and bs.actor_type='driver' and bs.booking_id = bookings.id) END   and service_code in (21,0,22,23,24,25,26,27,28,29,30,35,33,36,100,38,39,40,41,37,32,44,45))   and state='open'  and ( ( 
//    ST_DistanceSphere(pickup_geom, ST_GeomFromText('POINT(67.080777 24.8667537)',4326))/ 1000 < 2 and CURRENT_TIMESTAMP <= dt + interval '10 seconds' or
//    ST_DistanceSphere(pickup_geom, ST_GeomFromText('POINT(67.080777 24.8667537)',4326))/ 1000 < 3 and CURRENT_TIMESTAMP <= dt + interval '20 seconds' or 
//    ST_DistanceSphere(pickup_geom, ST_GeomFromText('POINT(67.080777 24.8667537)',4326))/ 1000 < 3.5 and CURRENT_TIMESTAMP <= dt + interval '40 seconds' or
//    ST_DistanceSphere(pickup_geom, ST_GeomFromText('POINT(67.080777 24.8667537)',4326))/ 1000 < 5 and CURRENT_TIMESTAMP >= dt + interval '40 seconds' ) )
//    ORDER BY distance asc , case when bid_amount IS Not NULL then bid_amount end DESC 
//    limit 14