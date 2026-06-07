# Picking my dataset
I chose this dataset from the Chicago Data Portal because I like art wanted to learn more about public art in Chicago. I was hoping to find a more detailed dataset that had more information about public art installations around the city, but this was the closest I could get to that from the database. 
I went with this dataset in particular because it was the most recently updated with the most views out of several with similar names. 
# Examining the dataset
This dataset looks at public artworks in parks in the Chicagoland area. Its columns are: "the_geom","OBJECTID","PARK","PARK_NO","NAME","X_COORD","Y_COORD","ARTIST","OWNER","GISOBJID","OFFICIAL_N". 
Unfortunately, there is no data for any sort of time, nor type of artwork. This limited my visualizations to relational (in terms of the artwork ownership/creator) and spatial. 
With these limiations, I decided focus my data research question around w
Some columns are somewhat redunant for my visualization, such as the_geom X_COORD/Y_COORD, and NAME and OFFICIAL_N; I decided to just use X_COORD and Y_COORD, and ignored OFFICIAL_N as it wasn't as complete as NAME. 
I had to clean up some of the artist names; Frederick Cleveland Hibbarb was sometimes recorded as Frederick C. Hibbarb, and works with unknown artists were recorded as both Unknown and Unknown Artist. 
With these
# Methodology
After examining the dataset, I decided to focus my research question around: Where is Chicago's public art located, and how concentrated is it within the park system?
# Claude
Claude was used to help for some callback implementation, formatting, and to fix the labels for the treemap.