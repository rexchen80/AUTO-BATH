using System;

[Serializable]
public class Landmark
{
    public int id;
    public float x;
    public float y;
    public float z;
}

[Serializable]
public class LandmarkFrame
{
    public int frame;
    public Landmark[] landmarks;
} 