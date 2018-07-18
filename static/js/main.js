$(function() {
    $('.match').matchHeight();
});

// sticky header
function init() {
    window.addEventListener('scroll', function(e){
        var distanceY = window.pageYOffset || document.documentElement.scrollTop,
            shrinkOn = 100,
            header = document.querySelector("header#main");
        if (distanceY > shrinkOn) {
            classie.add(header,"shrink");
        } else {
            if (classie.has(header,"shrink")) {
                classie.remove(header,"shrink");
            }
        }
    });
}
window.onload = init();

//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiPGFub255bW91cz4iXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUE7RUFBQSxDQUFBLENBQUUsUUFBQSxDQUFBLENBQUE7SUFDQSxDQUFBLENBQUUsU0FBRixDQUFZLENBQUMsS0FBYixDQUFtQixRQUFBLENBQUEsQ0FBQTthQUNqQixDQUFBLENBQUUsTUFBRixDQUFTLENBQUMsTUFBVixDQUFBO0lBRGlCLENBQW5CO1dBRUEsQ0FBQSxDQUFFLFFBQUYsQ0FBVyxDQUFDLE9BQVosQ0FBb0IsUUFBQSxDQUFDLENBQUQsQ0FBQTtBQUNsQixVQUFBLFNBQUEsRUFBQTtNQUFBLFNBQUEsR0FBWSxDQUFBLENBQUUsUUFBRjtNQUNaLEtBQUEsR0FBUSxDQUFBLENBQUUsTUFBRjtNQUNSLElBQVUsU0FBUyxDQUFDLEVBQVYsQ0FBYSxDQUFDLENBQUMsTUFBZixDQUFBLElBQTBCLFNBQVMsQ0FBQyxHQUFWLENBQWMsQ0FBQyxDQUFDLE1BQWhCLENBQXVCLENBQUMsTUFBNUQ7QUFBQSxlQUFBOzthQUNBLEtBQUssQ0FBQyxJQUFOLENBQUE7SUFKa0IsQ0FBcEI7RUFIQSxDQUFGO0FBQUEiLCJzb3VyY2VzQ29udGVudCI6WyIkIC0+IFxuICAkKCcudG9nZ2xlJykuY2xpY2sgLT4gXG4gICAgJCgnLnRpcCcpLnRvZ2dsZSgpXG4gICQoZG9jdW1lbnQpLm1vdXNldXAgKGUpIC0+XG4gICAgY29udGFpbmVyID0gJChcIi5zaGFyZVwiKVxuICAgIHBvcHVwID0gJCgnLnRpcCcpXG4gICAgcmV0dXJuIGlmIGNvbnRhaW5lci5pcyhlLnRhcmdldCkgb3IgY29udGFpbmVyLmhhcyhlLnRhcmdldCkubGVuZ3RoXG4gICAgcG9wdXAuaGlkZSgpIl19
//# sourceURL=coffeescript