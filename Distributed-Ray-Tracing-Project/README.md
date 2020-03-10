# Instructions
Many problems that we want to solve in Computer Science are "easy" to split up into smaller parts. [Ray 
tracing](https://en.wikipedia.org/wiki/Ray_tracing_(graphics)) is one example of this (at least for our simple case).

# How Ray Tracing Works
Our very simple ray tracer starts with a scene that has things, lights, and a camera. To fill each pixel 
in our image we project a ray from the camera and see what thing the ray hits first. That object (we are 
limited to a sphere and plane) will have some surface properties that describe how light interacts with 
it. We could, at this point, use the surface property as a color and use that for the image. To make 
things more realistic, we look at how each light in the scene interacts with our intersection point on 
the thing. We also consider a new ray corresponding to what would be seen if the surface had a mirror-
like finish. This second ray is computed in the same way as the first. We could bounce like this 
forever, but it would take forever, so we limit to some maximum number of bounces. These all add up to 
the color for the pixel.

# Distributed Ray Tracing
Two aspects of ray tracing conspire to make it good for our project:
1. Each pixel is computed independently.
2. The scene description is significantly small.

Each pixel as an independent computation means that we can perform that computation anywhere where we 
have access to the scene description. With a compact scene description, it is feasible to transmit 
the scene quickly. Our design will be client server where the client gives the server work to do: a 
scene and specific pixels to work on. The server works on the pixels and notifies the client when the 
work is completed. The client will also need to get the completed pixel colors.

Clients should be able to connect to as many servers as are available to do work.

# Implementation
You can download the starting code and test to see that the code for your language of choice is 
functioning as expected by running it with the --demo command line flag:

IN PROGRESS
