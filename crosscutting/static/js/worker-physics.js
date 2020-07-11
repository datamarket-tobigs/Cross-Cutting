// helpers
importScripts("cannon.build.js");
function random(min, max) {
    if (!min) {
        min = 1;
    }
    if (!max) {
        max = min;
        min = 0;
    }
    return (Math.random() * (max - min) + min);
}

function smoothstep(min, max, value) {
    var x = Math.max(0, Math.min(1, (value-min)/(max-min)));
    return x*x*(3 - 2*x);
};

function customCurve(x) {
    return smoothstep(0., .15, x) * (1. - Math.pow(Math.max(0., Math.abs(x) * 2. - 1.), 10.));
}

// setup world
let world = new CANNON.World();
world.broadphase = new CANNON.SAPBroadphase(world);
world.gravity.set(0,0,0);
// world.solver.tolerance = 0.1;
const worldPoint = new CANNON.Vec3(0,0,0);

// sphere config
const sphereMass = 300;
let sphereShape = new CANNON.Sphere(1);
let sphereMaterial = new CANNON.Material('');
sphereMaterial.friction = 0;

let spheres = [];

// move config
let moveBody = new CANNON.Body({
    mass: sphereMass,
    shape: new CANNON.Sphere(1),
    position: new CANNON.Vec3(0,0,0),
    fixedRotation: true
});
world.addBody(moveBody);

function resetBody(body) {
    // random starting position
    body.position.set(
        moveBody.position.x + random(-1,1),
        moveBody.position.y + random(-1,1),
        moveBody.position.z + random(-1,1)
    );
    // random starting angle
    body.quaternion.setFromAxisAngle(new CANNON.Vec3(random(1),random(1),random(1)), random(-180,180));
    // random impulse
    body.applyLocalImpulse(new CANNON.Vec3(30,30,30), new CANNON.Vec3(random(-30,30),random(-30,30),random(-30,30)));
    body.shapes[0].radius = 0.001;
    return body;
}

let body;
let scale;
let age;
let life;
let p;
let q;

let attractForce = new CANNON.Vec3();

self.onmessage = function(e) {

    let positions = e.data.positions;
    let quaternions = e.data.quaternions;
    let scales = e.data.scales;

    // this.console.log(e);

    moveBody.position.set(e.data.mouse.x, e.data.mouse.y, e.data.mouse.z);

    if (e.data.create) {
        let i = spheres.length;
        body = new CANNON.Body({
            mass: sphereMass,
            shape: new CANNON.Sphere(1),
            angularDamping: 0.2,
            linearDamping: .01,
            material: sphereMaterial
        });

        body = this.resetBody(body);

        // add to lists
        spheres.push(body);
        scales[4*i + 0] = 0.001; // scale
        scales[4*i + 1] = 0; // age
        scales[4*i + 2] = random(50,500); // life
        scales[4*i + 3] = 0; // velocity
        world.addBody(body);
    }
    // Step the world
    world.step(e.data.dt);

    for (var i = 0; i < spheres.length; i++) {
        body = spheres[i];
        scale = scales[4*i+0];
        age = scales[4*i+1];
        life = scales[4*i+2];
        scale = customCurve(age/life) * this.Math.max(1.-(life / 500), .5);
        // increase age
        age++;
        // reset after death
        if (age>life) {
            scale = 0.001;
            age = 0;
            life = random(50,500);
            body = this.resetBody(body);
        }
        // set scale
        body.shapes[0].radius = scale;
        // move spheres to center
        attractForce.set(
            (e.data.mouse.x - body.position.x) * 700,
            (e.data.mouse.y - body.position.y) * 700,
            (e.data.mouse.z - body.position.z) * 700
        );
        body.applyForce(attractForce, worldPoint);
        // save data
        p = body.position;
        q = body.quaternion;
        positions[3*i + 0] = p.x;
        positions[3*i + 1] = p.y;
        positions[3*i + 2] = p.z;
        quaternions[4*i + 0] = q.x;
        quaternions[4*i + 1] = q.y;
        quaternions[4*i + 2] = q.z;
        quaternions[4*i + 3] = q.w;
        // ensure scale data is saved
        scales[4*i + 0] = scale;
        scales[4*i + 1] = age;
        scales[4*i + 2] = life;
        scales[4*i + 3] = body.velocity.clone().length();

    }
    // Send data back to the main thread
    self.postMessage({
        create: e.data.create,
        positions: positions,
        quaternions: quaternions,
        scales: scales
    }, [positions.buffer,
        quaternions.buffer,
        scales.buffer]);
        
};