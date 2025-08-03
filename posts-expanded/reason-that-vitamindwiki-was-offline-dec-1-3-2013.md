{
    "title": "Reason that VitaminDWiki was offline Dec 1-3, 2013",
    "slug": "reason-that-vitamindwiki-was-offline-dec-1-3-2013",
    "aliases": [
        "/Reason+that+VitaminDWiki+was+offline+Dec+1-3+2013",
        "/4855"
    ],
    "tiki_page_id": 4855,
    "date": "2013-12-04",
    "tags": []
}


### Domain Name System Address Error

In the middle of November VitaminDWiki moved from <span>[www.Hostmonster.com]</span> to <span>[www.ElasticHost.com]</span> and <span>[www.Cloudways.com]</span>

The Domain Name System (DNS) was updated then to point to the new locations.

In the third week of November VitaminDWiki was erased from Hostmonster

&nbsp; &nbsp;So far, so good.

In early December, for some random or malicious reason, Hostmonster apparently sent a message to DMS reverting the location pointer back to itself

The DNS system then was updated with the old, nonfunctional, address

After much detective work and experiments with the help of Cloudways the problem was found and solved.

The DNS system was updated with the correct pointer, which you can see at [https://www.whatsmydns.net/#A/VitaminDWiki.com](https://www.whatsmydns.net/#A/VitaminDWiki.com)

The DNS system takes about 30 hours to update all of the pointers around the world.

 **Reason for moving to the new host** 

VitaminDWiki had outgrown the ability of Hostmonster to deal with the number of visitors

ElasticHost is, as you might guess from its name, able to elastically adjust to increased traffic needs - by > 1000X if needed