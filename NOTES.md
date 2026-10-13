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
 Transmission: Manual 6-spd
 Offical figures Rounded: city08:31, highway08:42, comb08:35, 
 Offical figures Unrounded: city08:30.9997, highway08:42.1485, comb08:35.1882, 
 Real world summary: avgMPG:38.280173986, recordcount:2, cityPercent:51, highwayPercent:49, maxMpg:46, minMpg:33,  
 Driver record1:Mpg:46.2, cityPercent:20, highwayPercent:80 , lastdate: 2018-02-23T00:00:00-05:00
 Driver record2:Mpg:32.678302361, cityPercent:83, highwayPercent:18, lastdate: 2018-01-04T00:00:00-05:00

 ID: 38247
 2.0 NA CVT Auto results:
 Engine Type: Naturally Aspirated NA
 Transmission:Automatic (variable gear ratios) CVT
 Offical figures Rounded: city08:28, highway08:40, comb08:32, 
 Offical figures Unrounded: city08:28.0, highway08:40.0499, comb08:32.3846, 
 Real world summary: avgMPG:57.0, recordcount:1, cityPercent:10, highwayPercent:90, maxMpg:57, minMpg:57,  
 Driver record:Mpg:57, cityPercent:10, highwayPercent:90, recordCount: 1, lastdate: 2020-05-30T00:00:00-04:00
Side note: no results for manual 2.0 NA engine

The comparisons of these two results show that the gap for Naturally Aspirated engines and Turbocharged is massive, however these results tell me a lot and nothing at the same time.
First off, the sample used for the Civics is tiny, there is a total of 3 driver records, which indicates that there should be a minimun recordCount before using a vehicles real-world figures.
The next point is that the 57mpg figure for 2.0 NA engine is most likey an outlier of a result. This is well above the the car's offical highway figure of 40mpg. There could be a few factors for this figure, a data entry mistake, someone driving extremely economical or even a short sample.For the process of cleaning the data, i will most likey flag any extreme outliers, as excluding them is not accurate as it may actually be achievable in some rare cases. 

Another finding was the driving mix between the two engine types. The NA driver did 90% highway miles, which is unfair to compare against the 49% and 18% for the driver record of the 1.5T engines. Using the comb08 as the measurement for this isn't fair, so i will most likey calculate the offical figure for each driver's own mix, resulting in the harmonic mix.

Another comparision is the transmission types. A manual and an CVT transmission differ in gearboxes, which is an example of a cofounder in this case.

 
 13 Oct: explored 1.5t and 2.0 NA engines, 1.5t manuel ID 38248, 2.0 NA Auto ID 38247

