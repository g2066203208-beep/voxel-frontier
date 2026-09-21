#pragma once
#include <cmath>
#include <algorithm>

namespace fb {

struct Vec2 { float x=0, y=0; };
struct Vec3 {
    float x=0,y=0,z=0;
    Vec3 operator+(const Vec3& o) const { return {x+o.x,y+o.y,z+o.z}; }
    Vec3 operator-(const Vec3& o) const { return {x-o.x,y-o.y,z-o.z}; }
    Vec3 operator*(float s) const { return {x*s,y*s,z*s}; }
};
inline float dot(Vec3 a,Vec3 b){ return a.x*b.x+a.y*b.y+a.z*b.z; }
inline Vec3 cross(Vec3 a,Vec3 b){ return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
inline float length(Vec3 v){ return std::sqrt(dot(v,v)); }
inline Vec3 normalize(Vec3 v){ float l=length(v); return l>1e-6f?v*(1.f/l):Vec3{}; }

struct Mat4 { float m[16]{}; };

inline Mat4 identity(){
    Mat4 r{}; r.m[0]=r.m[5]=r.m[10]=r.m[15]=1.f; return r;
}
inline Mat4 mul(const Mat4& a,const Mat4& b){
    Mat4 r{};
    for(int c=0;c<4;c++) for(int row=0;row<4;row++)
        r.m[c*4+row]=a.m[0*4+row]*b.m[c*4+0]+a.m[1*4+row]*b.m[c*4+1]+a.m[2*4+row]*b.m[c*4+2]+a.m[3*4+row]*b.m[c*4+3];
    return r;
}
inline Mat4 perspective(float fovy,float aspect,float zn,float zf){
    float f=1.f/std::tan(fovy*0.5f);
    Mat4 r{};
    r.m[0]=f/aspect; r.m[5]=f; r.m[10]=(zf+zn)/(zn-zf); r.m[11]=-1.f;
    r.m[14]=(2.f*zf*zn)/(zn-zf);
    return r;
}
inline Mat4 lookAt(Vec3 eye,Vec3 center,Vec3 up){
    Vec3 f=normalize(center-eye), s=normalize(cross(f,up)), u=cross(s,f);
    Mat4 r=identity();
    r.m[0]=s.x; r.m[4]=s.y; r.m[8]=s.z;
    r.m[1]=u.x; r.m[5]=u.y; r.m[9]=u.z;
    r.m[2]=-f.x; r.m[6]=-f.y; r.m[10]=-f.z;
    r.m[12]=-dot(s,eye); r.m[13]=-dot(u,eye); r.m[14]=dot(f,eye);
    return r;
}

struct Color { float r=1,g=1,b=1,a=1; };
inline Color mix(Color a,Color b,float t){ return {a.r+(b.r-a.r)*t,a.g+(b.g-a.g)*t,a.b+(b.b-a.b)*t,a.a+(b.a-a.a)*t}; }
inline Color mul(Color c,float f){ return {c.r*f,c.g*f,c.b*f,c.a}; }
inline float clamp01(float v){ return std::clamp(v,0.f,1.f); }

} // namespace fb
