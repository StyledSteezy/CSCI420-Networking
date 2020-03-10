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
```
$ python raytracer.py --demo
... some time passes
$ ls
demo.ppm  raytracer.py
```
The output from the demo is a ppm file which is a text based image format (easy to write). There is not broad support for this format, 
but it is easy to convert using ImageMagick:
```
$ magick convert demo.ppm demo.png
```
There is also a javascript based converter: [http://paulcuth.me.uk/netpbm-viewer/]().

Once you have verified that the starting code is working, you should design how your client and servers are going to communicate. We 
will only be using UDP to communicate in the project The server programs are likely to be simpler and the client will be more 
complicated as it must coordinate and account for the work to be done while the server does the work. The client may also do work while 
waiting for results.

Start by communicating the scene information from client to server. You will notice that the text-based file format for scenes has a 
potentially very helpful feature: the order of individual lines of the file does not matter.

Next communicate the work to be done. Note the trade-offs here. On the one hand, you could communicate for each individual pixel. The 
communication overhead may be more then it would take to just render the pixel on a single machine. On the other end, you could divide 
the whole scene up evenly for each server. This could leave some servers idle if they happen to get mostly pixels that hit nothing while 
others max out bounces for every pixel.

On the server program modify the

render

function to do just the work requested. Figure out how to send the data back.
Expand the client program to be able to manage multiple servers at once. This will require more difficult concurrent programming that I 
can walk you through.

Once things appear to be working, start tackling robustness. Will your program work if one of the servers gets disconnected? What if the 
client disappears? Will it work of a server is delayed for a while, but then comes back? What if a UDP message arrives twice? Out of 
order? Not at all? Work through these possibilities by drawing sequence diagrams that clearly show how each scenario will work.

We will discuss further details in class about managing servers on our network in a way that will minimize interference.

# Project Requirements
Your goal is to speed up the wall-clock time it takes to do ray tracing. We will test each program on a scene that takes your language 
about a minute and a half to perform on a single machine. Calculate the [speedup](https://en.wikipedia.org/wiki/Speedup) from a 
successful run of your system on our network. In addition, track the number of bytes received and sent by your client. How much 
bandwidth was demanded by your work?

# Write Up
The goal for this project was to improve the wall clock time that it takes to do ray tracing.
For our example, we are given a scene that has things like spheres, lights, and cameras, etc. The
ray-tracing will generate an image by tracing the path of the light produced by the camera to see
what it will hit within the scene. In our case, the light will hit spheres and the reflective ground.
When the ray hits the stuff in the scene we record how the light in the scene intersects with that
stuff. This information is stored as RGB pixels where red, green, and blue are all 8 bits, therefore
having a range of 0 to 255 integer values each.

Each pixel is computed independently. Because of this, we can perform the computation
when and wherever we have the scene data. For the project, if we have a client and a single
server we will transfer the scene data from the client to the server, have the server do the work,
then send back the computed pixels to the client. The main objective is to improve the wall-clock
time by splitting up the computations to multiple servers and have the different servers do a part
of the work and then send back the computed pixels to the client. The client will then combine
all that it has received from the servers into one finished piece.

Data will be sent back and forth between the client and the server as packets. We had to
use UDP which is an unreliable connection. Therefore we need to take into account when
packets are dropped, duplicated, or received out of order. To ensure all of the data made it to the

desired destination we recorded the total number of packets being sent and if the packets are not
received then resend and try again. This ended up being a good approach and eventually, all the
data would end up where we wanted. Although, it was not reliable on how much time it would
take. For example, if packets keep being dropped then they needed to be resent every time. This
partially left the performance up to chance because we cannot ensure that the packets will not be
dropped.

The first approach for dividing the work onto different servers was to split the scene up
into quadrants allowing each server to take a quadrant to perform work on. We quickly realized
that this approach would not work because the number of servers had to be 4. Therefore we
changed our approach and split up the scene data on the x-axis so the servers work would be
somewhat distributed evenly. The client now sends out packets of the scene to multiple servers
that is split on the x-axis. To indicate which packet has which data we made a tuple to hold the
part number, total parts, and the message. Each server will indicate which piece it will work on
and out of the total number of pieces. Note that we also printed this information allowing the
user to see how many servers are working and how many pieces the scene has been broken into.

Each server will then do some of the work and send it back to the client. The client will
then receive the finished data and combine all the pieces into one. In the end, we were able to
finish the project and accomplish our goal of improving the wall-clock time that it takes to do ray
tracing by distributing the work over multiple servers. Although, splitting up the work on more
than a certain amount of servers does not guarantee an improvement in time.

# Analysis
600x600 scene

Running with 1 server:
- Render time = 157 seconds
- Wall-clock time = 171 seconds

Running with 3 servers:
- Average render time = 59 seconds
- Wall-clock time = 117 seconds

Running with 7 servers: try #1
- Average render time = 33 seconds
- Wall-clock time = 319 seconds

Running with 7 servers: try #2
- Average render time = 30 seconds
- Wall-clock time = 344 seconds

Running with 7 servers: try #3
- Average render time = 35 seconds
- Wall-clock time = 314 seconds

# Observations
Running 3 servers vs 1 server:
- Improvement = 54 seconds. This is good and shows that because the work is being distributed
there is a significant improvement.

Running 7 servers vs 3 servers:
- The average rendering time for each server is improved, which was expected because the scene
is broken up into smaller pieces, allowing each server to do less work. Although, the wall-clock
time was much better with 3 servers opposed to 7 servers. I hypothesize that this is happening
because more packets need to be sent from the server to the client. Which means that the chances
of packets being dropped increases. When the packets are dropped the server needs to resend
them, which takes time, therefore lowering the performance.

# Contributors
Christian Tomford, Caleb Lyon, and Mohammad Pahlevan
