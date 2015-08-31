#pragma once



namespace mockup {


// Allows to have a list of pointers to drawable objects
class GLDrawable
{
public:
    GLDrawable() = default;
    virtual ~GLDrawable() = default;
    virtual void draw() = 0;
};


}
