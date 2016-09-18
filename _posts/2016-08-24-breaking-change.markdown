---
layout: post
title: "breaking change"
date: "2016-08-24 18:16:53 +0300"
category: seeds
tag : codeing
published: true
author: Lee Elenbaas
---
# Definition

Those are my own definitions, that i know intuitively:

- If you have a service: any change that can break a client implementation without him changing anything.

- In a library or code: any API or behavior change that will force users of the API to change their code in order to continue using a new version.

You can find more dictionary like definition on [Wiktionary](https://en.wiktionary.org/wiki/breaking_change)

# Identification

I identifying a breaking change is hard on developers since it force us to wear the hat of the user who uses our code.

Good testing culture, one that force creating unit tests (TDD anyone?) and UI automation tests helps in that regard. Makes it easier on the developer see the other direction, simply since he supposed to see it as part of his day to day job.

But even in the world of code to code APIs - breaking changes slip through unidentified simply since the language customers use and that used by the developers is usually not the same language.

In the world of on-line services and UI things are a lot worse.

# Why do it?

Breaking changes to API is like refactoring to implementation.

If you do it in the correct amount, at the correct time, it helps your code grow.

If you do it at the wrong places, you end up costing to much to your customers that they will start abandoning your code/service and move on to other greener libraries/services.

Breaking changes can be forced on you for security reasons, design flows that needs to be corrected, unintuitive API/behavior that makes it harder than necessary to use your code/service.

They can be done as part of a new design or new vision. And they have the potential of opening new uses for your code that were closed before.

# The right way

As with anything there is no one right way, but there are guideline:

- Since customers are paying the price, you need to notify them as early as possible, help them prepare.

- Always assume that there is a customer that will be hurt from that change, so try and identify them before hand and fix it with them in advance.

- If you can support multiple versions (using multiple/versioned APIs, or package management or any other means) do it and leave the old versions functional for a while.

- If possible deprecate the old behavior before you actually break it.

And even doing all that, breaking changes will have their price.

# Culture

The hard part about breaking changes is not to define them, or identify them.
It is making a sensible behavior around them.

- Create a culture that accept their role in your product.

- Understand and gives the place for the price that comes with those changes on the clients.

- Encourage everyone on the pipe to identify and communicate the breaking change and its price.

- And then implement the guidelines in the correct way for your project.
