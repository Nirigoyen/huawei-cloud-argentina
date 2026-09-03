import java.util.List;
import java.util.ArrayList;

public class UserService {
    private List<User> users = new ArrayList<>();

    public void addUser(User user) {
        users.add(user);
    }

    // BUG: May return null, callers must handle null
    public User findUser(String name) {
        for (User u : users) {
            if (u.getName().equals(name)) {  // NPE if u.getName() is null
                return u;
            }
        }
        return null;
    }

    // BUG: NPE if user not found, or if email is null
    public String getUserEmail(String name) {
        User user = findUser(name);
        return user.getEmail();  // NPE if user is null or email is null
    }

    // BUG: NPE chain: user -> address -> city
    public String getUserCity(String name) {
        User user = findUser(name);
        Address addr = user.getAddress();  // NPE if user is null
        return addr.getCity();  // NPE if address is null or city is null
    }

    // BUG: Multiple NPE risks
    public String formatUserInfo(String name) {
        User user = findUser(name);
        String email = user.getEmail();  // NPE
        String city = user.getAddress().getCity();  // NPE chain
        return name + " (" + email + ") from " + city;
    }
}

class User {
    private String name;
    private String email;
    private Address address;

    public User(String name, String email, Address address) {
        this.name = name;
        this.email = email;
        this.address = address;
    }

    public String getName() { return name; }
    public String getEmail() { return email; }
    public Address getAddress() { return address; }
}

class Address {
    private String street;
    private String city;
    private String zipCode;

    public Address(String street, String city, String zipCode) {
        this.street = street;
        this.city = city;
        this.zipCode = zipCode;
    }

    public String getStreet() { return street; }
    public String getCity() { return city; }
    public String getZipCode() { return zipCode; }
}
