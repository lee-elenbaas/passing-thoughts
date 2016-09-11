---
layout: post
category: "blog"
title: "No spaces?!"
tag: "codeing"
published: true
---
# Readability

I am a firm believer of making code readable.

Readable code helps everyone, including the person who wrote it, to get into the code.
Makes it easier to understand the logic, easier to fix bugs when you need to, and easier to re-factor if necessary.

There are basically two approaches:

 * Make it readable to everyone - by making it as simple as possible and as close as possible to English.
 * Make it follow a project convention.

You can see that the first option is a specific case of the second. Only the convention is very low level, with the attempt to target as many people as possible.

Up until now I always practiced the first option. Both in the companies i worked for and in my personal projects. And was confident that this is the correct route to go by. Right now i am in a company where i need to learn the convention used by the company.
And this forced me to rethink my approach.

When I look at large projects, they all develop their own convention. Even if the developers strive to keep the code readable to everyone. The introduction of library functions, utilities, custom markup tags... all generates a new convention, one that is project specific.
Anyone who try to get into a large project, have to understand enough of those project specific building blocks in order to be productive.

On the other hand, right now I have to face one of the steepest learning curves i have ever had to climb due to this project specific convention that I have to get used to.

In my case the major thing i have to get used to is condensed code. No spacing, no unnecessary characters, no comments, no empty lines.
And did i say it before: no spaces. even between sections of code that have different roles.

# Comparing apples and oranges

When you compare the two approaches you get the following table:

|                | English like    | Project specific |
|----------------|-----------------|------------------|
| Audience       | Wide            | Narrow           |
| Learning curve | Low             | High             |
| Code size      | Higher          | Minimal          |

Lets look at each factor.

## Audience

For projects that target wide audience. Educational projects, open source project, the wider the audience who can read the code, the better.
For closed in house projects, the company really care only that the people inside the company will be able to easily get into the code, so it becomes a non-issue for them. Unless they have plans to open the code up in the future.

## Learning curve

This is a clear cut.
In every project, people change and new people need to come in. The steeper the learning curve is, the harder it is to get new people into it.

## Code size

This is another clear cut. Smaller code means less bugs, and less to read and understand.

# Conclusion

The bottom line is that whatever you will go by, you will make a compromise.
Just make the right compromise for the project you are working on.
