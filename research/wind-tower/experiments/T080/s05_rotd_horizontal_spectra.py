"""Two-horizontal-component oscillator spectra; research method, not record validation.
Input acceleration in m/s^2; dt in seconds; periods in seconds.
Newmark average acceleration (beta=1/4, gamma=1/2), zero initial state.
RotD50/100: median/maximum of directional PSA maxima at 180 one-degree orientations.
"""
import math
import statistics

def _psa(ax, dt, period, damping=0.05):
    if not (period > 0 and dt > 0 and 0 <= damping < 1):
        raise ValueError('invalid period, dt or damping')
    if len(ax) < 2 or any(not math.isfinite(x) for x in ax):
        raise ValueError('invalid acceleration array')
    w=2*math.pi/period; k=w*w; c=2*damping*w
    b=0.25; g=0.5
    a0=1/(b*dt*dt); a1=g/(b*dt); a2=1/(b*dt)
    a3=1/(2*b)-1; a4=g/b-1; a5=dt*(g/(2*b)-1)
    ke=k+a0+a1*c
    u=v=0.; acc=-ax[0]; peak=0.
    for ag in ax[1:]:
        force=-ag+a0*u+a2*v+a3*acc+c*(a1*u+a4*v+a5*acc)
        un=force/ke
        an=a0*(un-u)-a2*v-a3*acc
        vn=v+dt*((1-g)*acc+g*an)
        u,v,acc=un,vn,an
        peak=max(peak,abs(u))
    return peak*w*w

def rotd(east, north, dt, periods, damping=0.05, angle_step=1):
    if len(east)!=len(north) or len(east)<2 or 180%angle_step:
        raise ValueError('component length or angular step')
    if any(not math.isfinite(v) for v in east+north):
        raise ValueError('nonfinite input')
    result=[]
    for T in periods:
        values=[]
        for deg in range(0,180,angle_step):
            theta=math.radians(deg)
            a=[math.cos(theta)*x+math.sin(theta)*y for x,y in zip(east,north)]
            values.append(_psa(a,dt,T,damping))
        result.append((T,statistics.median(values),max(values),min(values)))
    return result

def _tests():
    dt=0.01; t=[i*dt for i in range(1001)]
    e=[0.8*math.sin(2*math.pi*0.8*x) for x in t]
    n=[0.4*math.cos(2*math.pi*1.3*x) for x in t]
    base=rotd(e,n,dt,[0.5,1.,2.],angle_step=5)
    rotated=rotd(n,[-x for x in e],dt,[0.5,1.,2.],angle_step=5)
    for a,b in zip(base,rotated):
        assert all(abs(x-y)<1e-10 for x,y in zip(a,b)),(a,b)
        assert a[3]<=a[1]<=a[2]
    doubled=rotd([2*x for x in e],[2*x for x in n],dt,[1.],angle_step=5)
    assert abs(doubled[0][1]-2*base[1][1])<1e-10
    assert rotd([0.]*10,[0.]*10,dt,[1.])[0][2]==0
    try: rotd([0.]*3,[0.]*2,dt,[1.]); raise AssertionError('missing reject')
    except ValueError: pass
    for a in base: print('T=%.2f s RotD50=%.9f RotD100=%.9f min=%.9f m/s2'%a)
    print('PASS: 90-degree invariance, homogeneity, ordering, zero, length rejection')
if __name__=='__main__': _tests()


def rotd100_continuous(east, north, dt, periods, damping=0.05):
    """Exact continuous-azimuth RotD100 on the sampled Newmark displacement grid.

    Max over azimuth and sampled time commute:
    max_theta max_t |uE(t)cos(theta)+uN(t)sin(theta)|
      = max_t hypot(uE(t),uN(t)).
    The result is exact in azimuth but NOT exact between time samples.
    """
    if len(east) != len(north) or len(east) < 2:
        raise ValueError('component length')
    if not (math.isfinite(dt) and dt > 0 and
            math.isfinite(damping) and 0 <= damping < 1):
        raise ValueError('dt or damping')
    if any(not math.isfinite(x) for x in east) or any(
            not math.isfinite(x) for x in north):
        raise ValueError('nonfinite acceleration')
    output = []
    for T in periods:
        if not (math.isfinite(T) and T > 0):
            raise ValueError('period')
        w = 2 * math.pi / T
        k = w * w
        c = 2 * damping * w
        beta = 0.25
        gamma = 0.5
        a0 = 1 / (beta * dt * dt)
        a1 = gamma / (beta * dt)
        a2 = 1 / (beta * dt)
        a3 = 1 / (2 * beta) - 1
        a4 = gamma / beta - 1
        a5 = dt * (gamma / (2 * beta) - 1)
        ke = k + a0 + a1 * c
        states = [[0.0, 0.0, -axis[0]] for axis in (east, north)]
        peak = 0.0
        for ae, an in zip(east[1:], north[1:]):
            displacement = []
            for state, ag in zip(states, (ae, an)):
                u, v, acc = state
                un = (-ag + a0*u + a2*v + a3*acc
                      + c*(a1*u + a4*v + a5*acc)) / ke
                accn = a0*(un-u) - a2*v - a3*acc
                vn = v + dt*((1-gamma)*acc + gamma*accn)
                state[:] = [un, vn, accn]
                displacement.append(un)
            peak = max(peak, math.hypot(*displacement))
        output.append((T, peak * k))
    return output


def _continuous_tests():
    dt = 0.01
    t = [i * dt for i in range(1001)]
    east = [0.8*math.sin(2*math.pi*0.8*x) for x in t]
    north = [0.4*math.cos(2*math.pi*1.3*x) for x in t]
    periods = [0.5, 1.0, 2.0]
    exact = rotd100_continuous(east, north, dt, periods)
    for step in (1, 5, 15):
        grid = rotd(east, north, dt, periods, angle_step=step)
        lower = math.cos(math.radians(step/2))
        for (_, true), (_, _, sampled, _) in zip(exact, grid):
            assert sampled <= true + 1e-10
            assert sampled >= lower*true - 1e-10
    assert rotd100_continuous(north, [-x for x in east], dt, periods) == [
        (T, v) for T, v in exact
    ] or all(abs(a[1]-b[1]) < 1e-10 for a,b in zip(
        exact, rotd100_continuous(north, [-x for x in east], dt, periods)))
    assert all(abs(b[1]-2*a[1]) < 1e-10 for a,b in zip(
        exact, rotd100_continuous([2*x for x in east],
                                  [2*x for x in north], dt, periods)))
    assert rotd100_continuous([0.]*10, [0.]*10, dt, [1.])[0][1] == 0.
    for bad in (([float('nan')]*3, [0.]*3, 0.01, [1.]),
                ([0.]*3, [0.]*2, 0.01, [1.]),
                ([0.]*3, [0.]*3, 0.0, [1.]),
                ([0.]*3, [0.]*3, 0.01, [0.])):
        try:
            rotd100_continuous(*bad)
        except ValueError:
            continue
        raise AssertionError('invalid input accepted')
    print('PASS: exact sampled-time continuous-azimuth RotD100, '
          'grid enclosure, rotation, scale, zero, invalid-input rejection')
    for T, val in exact:
        print('T=%.2f s continuous RotD100=%.9f m/s2' % (T, val))


if __name__ == '__main__':
    _continuous_tests()
