##This project is answering the question of "Comparing the offical data to the real world MPG for turbocharged cars and naturally aspirated

Audience: someone buying a used car who is choosing between a small turbocharged engine and a larger naturally aspirated one, and wants to know whether the turbo's official MPG advantage holds up in real-world driving.

##API
The API studied for this project is from the U.S Deparment of Energy, does not require a key for access and it naturally returns XMl by default. 

To get the data returned as JSON instead, send the request header `Accept: application/json` 

https://www.fueleconomy.gov/

##Endpoints explored
https://www.fueleconomy.gov/ws/rest/vehicle/menu/year
 The returned XML from this endpoint is the year of  available models years. 

https://www.fueleconomy.gov/ws/rest/vehicle/menu/make?year=2020
The inputs for this endpoints is the year 2020, which returns values of different makes of vehicles for that year such as Aston Martini, Audi and etc.

https://www.fueleconomy.gov/ws/rest/vehicle/menu/model?year=2020&make=Ford
This endpoint returns the models for that year and the make.

https://www.fueleconomy.gov/ws/rest/vehicle/menu/options?year=2020&make=Ford&model=Mustang
The input for this endpoint is 2020, Ford and Mustang. The return endpoint outputs the style of transmission, the amount of cyclinders, engine size, turbocharged or naturally aspirated and a vehicle ID.
The vehicle ID is used for the next request to specify data for that particular vehicle 

https://www.fueleconomy.gov/ws/rest/vehicle/41952
This endpoint returns data such as the emission, fuel score, class of car and the urban and motoway MPG. It also returns whether users have uploaded any real MPG scores.

https://www.fueleconomy.gov/ws/rest/ympg/shared/ympgVehicle/41952
This endpoint return no results, there was no error 500 at all.


##Things i found
A malformed vehicle ID (e.g. with curly brackets) returns a 500 server error rather than a 400 (bad request) or 404 (not found). This means my script can't tell from the status code alone whether the server failed or I sent a bad request, so I can't just retry every 500. I'll need to validate IDs before sending them and limit how many times a failed request is retried.

https://www.fueleconomy.gov/ws/rest/vehicle/{41952}
This endpoint with curly brackets results in an server  error 500 - "There is a problem with the resource you are looking for, and it cannot be displayed"

I also found that when i requested for the real world MPG for 41952, there was no results, no error at all. This indicates that there is no entry for
 by drivers who have submitted their own figures regarding MPG. 

 From looking on,
 https://www.fueleconomy.gov/ws/rest/vehicle/41952
 a giveaway sign whether an vehicle has real world MPG figures is by seeing whether this field "mpgData" has values "Y" for yes and "N" for no. This tells in advance if a vehicle has real world MPG figures or not.
 
 So my script will only call the real-world MPG endpoint for vehicles where mpgData = Y, which avoids wasted requests. I will NOT drop the other vehicles from the dataset. I need them to measure coverage (what share of vehicles have real-world data) and to check whether turbo or naturally aspirated cars are better represented, which could bias the comparison.

 This API was decided over the MOT API as it did not require a key and a 5 day wait for approval. The MoT API requires the reg number for each lookup, whereas this API i can lookup any vehicle by usin the menu. In particular, it has direct turbo and supercharger fields, which is more suited to my question.


 12 Oct: explored the menu endpoints, found the mpgData field.

ID: 38248
 1.5T 6s manual results:
 Engine Type: TurboCharged
 Offical figures Rounded: city08:31, highway08:42, comb08:35, 
 Offical figures Unrounded: city08:30.9997, highway08:42.1485, comb08:35.1882, 
 Real world summary: avgMPG:38.280173986, recordcount:2, cityPercent:51, highwayPercent:49, maxMpg:46, minMpg:33,  
 Driver record:Mpg:46.2, cityPercent:20, highwayPercent:80, recordCount: matches

 ID: 38246
 2.0 NA 6s Automatic results:
 Engine Type: Naturally Aspirated NA
 Offical figures Rounded: city08:28, highway08:40, comb08:32, 
 Offical figures Unrounded: city08:28.0, highway08:40.0499, comb08:32.3846, 
 Real world summary: avgMPG:57.0, recordcount:1, cityPercent:10, highwayPercent:90, maxMpg:57, minMpg:57,  
 Driver record:Mpg:57, cityPercent:10, highwayPercent:90, recordCount: matches
Side note: no results for manual 2.0 NA engine
 

 13 Oct: explored 1.5t and 2.0 NA engines, 1.5t manuel ID 38248, 2.0 NA Auto ID 38246

