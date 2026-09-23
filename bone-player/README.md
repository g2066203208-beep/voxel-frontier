# X2D Bone Player

Android skeletal animation player.

## ZIP format
A .zip contains project.json and PNG files.

project.json example:
{
  "width":1080,
  "height":1920,
  "duration":2.0,
  "bones":[
    {"id":"root","parent":null,"x":540,"y":960,"rotation":0,"length":0},
    {"id":"arm","parent":"root","x":0,"y":-200,"rotation":20,"length":220}
  ],
  "sprites":[
    {"bone":"arm","image":"arm.png","pivotX":20,"pivotY":60,"scale":1.0}
  ],
  "keyframes":{
    "arm":[
      {"time":0,"x":0,"y":-200,"rotation":-20},
      {"time":1,"x":0,"y":-200,"rotation":40},
      {"time":2,"x":0,"y":-200,"rotation":-20}
    ]
  }
}

All child bone x/y/rotation values are local to the parent bone.
