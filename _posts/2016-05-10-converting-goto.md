---
layout: post 
category: blog
title: "Converting goto"
tagline: 
tag : codeing
published: true
---
I am working on a task I thought have passed from the world:
Converting "goto" code to functional programming.
And I am doing it in modern Javascript code.

This was covered by articles over 20 years ago, see http://ieeexplore.ieee.org/xpl/articleDetails.jsp?tp=&arnumber=126773&url=http%3A%2F%2Fieeexplore.ieee.org%2Fxpls%2Fabs_all.jsp%3Farnumber%3D126773

The basics are the normal loops, conditionals, break and continue.

# Conversion rules

* If you have a goto that jumps forward can be replaced by a simple if on the code it jumps over. 

* A goto that jump backwards is converted to loop. either a do-while loop, or an infinite loop. 

* Several jumps forward with overlapping skipped code can be made using flags, each goto condition will set the appropriate flags, and the code execution will depend on the flags. 

* Multiple jumps backward can be replaced by a single infinite loop, and appropriate flags. 

In general, it is best to understand what the code tries to do. There is usually a better way then just make it work with the new tools. 
