! Source-order single-precision gage-220 G/T/E replay for S07 native 2 s.
! Numerical diagnostics only; not wind-only ownership or physics PASS.
program s07_dcm_gnu_real32_micro
  use iso_fortran_env, only: real32, real64
  implicit none
  integer :: ios, j, gage, node
  real(real64) :: tm, te
  real(real32) :: g(24), t(20), e(14), e0(14)
  real(real32) :: rg(3), z2(3), f(3), m(3), den(3), dm(3), arm(3)
  character(len=2048) :: line
  character(len=1) :: tag

  read(*,'(A)',iostat=ios) line
  if (ios /= 0) error stop 'MISSING_G_LINE'
  read(line,*,iostat=ios) tag,tm,gage,g
  if (ios /= 0 .or. tag /= 'G' .or. gage /= 220) error stop 'BAD_G_LINE'
  if (abs(tm-0.1875_real64)>1.0e-10_real64) error stop 'WRONG_TIME'
  read(*,'(A)',iostat=ios) line
  if (ios /= 0) error stop 'MISSING_T_LINE'
  read(line,*,iostat=ios) tag,te,gage,node,t
  if (ios /= 0 .or. tag /= 'T' .or. gage /= 220 .or. node /= 1120) error stop 'BAD_T_LINE'
  if (abs(te-tm)>1.0e-10_real64) error stop 'T_TIME_MISMATCH'
  rg=g(1:3); z2=t(15:17)
  f=t(3:5)-(z2*t(2)+t(9:11))*t(1)
  m=cross(t(12:14)-rg,f)+t(6:8)
  do j=0,900
    read(*,'(A)',iostat=ios) line
    if (ios /= 0) error stop 'MISSING_E_LINE'
    read(line,*,iostat=ios) tag,te,gage,node,e
    if (ios /= 0 .or. tag /= 'E' .or. gage /= 220 .or. node /= 220+j) error stop 'BAD_E_LINE'
    if (abs(te-tm)>1.0e-10_real64) error stop 'E_TIME_MISMATCH'
    if (j==0) then
      e0=e
    else
      den=e(3:5)-(z2*t(2)+e(6:8))*e(1)
      f=f+den*abs(e(2))
      dm=cross(e(9:11)-rg,den)+e(12:14)
      m=m+dm*abs(e(2))
    end if
  end do
  den=e0(3:5)-(z2*t(2)+e0(6:8))*e0(1)
  f=(f+den*0.5_real32*abs(e0(2)))*0.001_real32
  arm=t(18:20)*(0.25_real32*e0(2))
  dm=cross(arm,den)+e0(12:14)
  m=(m+dm*0.5_real32*abs(e0(2)))*0.001_real32
  write(*,'(A,1X,6(ES24.16E3,1X))') 'GNU_REAL32_S07', f, m
  write(*,'(A,1X,6(ES24.16E3,1X))') 'NATIVE_G_TARGET',g(13:18)
contains
  pure function cross(a,b) result(c)
    real(real32),intent(in) :: a(3),b(3)
    real(real32) :: c(3)
    c(1)=a(2)*b(3)-a(3)*b(2)
    c(2)=a(3)*b(1)-a(1)*b(3)
    c(3)=a(1)*b(2)-a(2)*b(1)
  end function
end program
